"""
Flask routes and request handlers.

This module contains the web interface routes using the new clean architecture
with proper dependency injection and domain models.
"""
from flask import Blueprint, render_template, request, current_app
import pathlib
import uuid
import logging

# New clean architecture imports
from app.services import RosterServiceFactory
from app.models.domain import ProcessingOptions
from app.config import get_config
# Legacy HTML generation (TODO: modernize this as well)
from sublib import prepare_html

# Create blueprint
bp = Blueprint('main', __name__)

# Get configuration
config = get_config()


@bp.route("/health")
def health_check():
    """Health check endpoint for monitoring and tests."""
    return {
        "status": "healthy",
        "service": "StrataScribe",
        "debug": current_app.config.get('DEBUG', False),
        "supported_extensions": list(current_app.config.get('SUPPORTED_EXTENSIONS', ['.ros', '.rosz']))
    }, 200


@bp.route("/", methods=["GET", "POST"])
def upload_file():
    """Handle file upload and roster processing."""
    # Mobile user agent detection
    accept = 'accept = ".ros, .rosz"'
    user_agent = request.headers.get("User-Agent", "").lower()
    is_mobile = any(agent in user_agent for agent in config.MOBILE_USER_AGENTS)
    if is_mobile:
        accept = ""

    if request.method == "POST":
        f = request.files["file"]
        file_ext = pathlib.Path(f.filename).suffix

        if file_ext in config.SUPPORTED_EXTENSIONS:
            random_filename = str(uuid.uuid4()) + file_ext
            
            try:
                # Create roster processing service
                roster_service = RosterServiceFactory.create_service(config)
                
                # Save uploaded file using our FileService
                file_info = roster_service.file_service.save_uploaded_file(f, random_filename)
                current_app.logger.info(f"Uploaded file: {file_info.filename} ({file_info.file_size} bytes)")
                
                # Parse processing options from form data
                options = ProcessingOptions.from_form_data(request.form)
                
                # Process the battlescribe file using our new service
                processing_result = roster_service.process_roster_file(random_filename, options)
                
                # Extract data from processing result
                phase_data = processing_result.phases
                units_data = processing_result.units
                all_stratagems = processing_result.all_stratagems
                
                # Generate HTML using existing template utilities
                html_phase = prepare_html.convert_to_table(phase_data)
                
                # Handle multi-detachment: units_data might be a list of dicts
                if isinstance(units_data, list):
                    html_units = "".join(
                        [
                            prepare_html.convert_units_to_divs(units_dict)
                            for units_dict in units_data
                            if isinstance(units_dict, dict)
                        ]
                    )
                else:
                    html_units = prepare_html.convert_units_to_divs(units_data)
                
                # Convert Stratagem domain objects to format expected by prepare_html
                stratagems_list = []
                for stratagem in all_stratagems:
                    # Convert domain object to dict format expected by legacy template
                    stratagem_dict = {
                        'name': stratagem.name,
                        'faction_id': stratagem.faction_id,
                        'type': stratagem.type,
                        'cp_cost': stratagem.cp_cost,
                        'legend': stratagem.legend,
                        'description': stratagem.description,
                        'phase': stratagem.phase,
                        'id': stratagem.id,
                        'detachment': stratagem.detachment or '',
                        'subfaction_id': stratagem.subfaction_id or ''
                    }
                    stratagems_list.append(stratagem_dict)
                        
                html_stratagems = prepare_html.convert_to_stratagem_list(stratagems_list)
                
                return render_template(
                    "report.html",
                    html_phase=html_phase,
                    html_units=html_units,
                    html_stratagems=html_stratagems,
                )
                
            except (ValueError, FileNotFoundError) as e:
                print(f"Error processing roster file: {e}")
                return render_template("upload.html", accept=accept, error=f"Error processing roster file: {e}")
            except ConnectionError as e:
                print(f"Network error: {e}")
                return render_template("upload.html", accept=accept, error="Network error: Unable to download game data. Please try again later.")
            except Exception as e:
                print(f"Unexpected error processing roster: {e}")
                return render_template("upload.html", accept=accept, error="An unexpected error occurred. Please check your roster file and try again.")
        else:
            return render_template("upload.html", accept=accept)

    if request.method == "GET":
        return render_template("upload.html", accept=accept)


@bp.route("/about", methods=["GET"])
def about_html():
    """Show about page."""
    return render_template("about.html")


# Services are now initialized on-demand through factories
# No global initialization needed with our new architecture