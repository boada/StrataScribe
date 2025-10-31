import os.path
import pathlib
import uuid

from flask import Flask, render_template, request

from sublib import wahapedia_db, battle_parse, prepare_html

# File Extensions
FILE_EXT_ROS = ".ros"
FILE_EXT_ROSZ = ".rosz"

app = Flask(__name__)

upload_directory = os.path.abspath("./battlescribe")


@app.route("/", methods=["GET", "POST"])
def upload_file():
    # adding file filter for mobile requests
    accept = 'accept = ".ros, .rosz"'
    user_agent = request.headers.get("User-Agent", "").lower()
    is_mobile = "mobile" in user_agent or "android" in user_agent
    if is_mobile:
        accept = ""

    if request.method == "POST":
        f = request.files["file"]
        file_ext = pathlib.Path(f.filename).suffix

        if file_ext == FILE_EXT_ROS or file_ext == FILE_EXT_ROSZ:
            random_filename = str(uuid.uuid4()) + file_ext
            
            try:
                # Ensure upload directory exists
                os.makedirs(upload_directory, exist_ok=True)
                f.save(os.path.join(upload_directory, random_filename))
                
                # Parse the battlescribe file
                json_phase, json_units, json_stratagems = battle_parse.parse_battlescribe(
                    random_filename, request.form
                )
                
                # Generate HTML output
                html_phase = prepare_html.convert_to_table(json_phase)
                
                # Handle multi-detachment: json_units is a list of dicts
                if isinstance(json_units, list):
                    html_units = "".join(
                        [
                            prepare_html.convert_units_to_divs(units_dict)
                            for units_dict in json_units
                            if isinstance(units_dict, dict)
                        ]
                    )
                else:
                    html_units = prepare_html.convert_units_to_divs(json_units)
                    
                html_stratagems = prepare_html.convert_to_stratagem_list(json_stratagems)
                
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


@app.route("/about", methods=["GET", "POST"])
def about_html():
    return render_template("about.html")


wahapedia_db.init_db()
battle_parse.init_parse()

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False)
