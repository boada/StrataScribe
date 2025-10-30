#!/usr/bin/env python3
"""
Test script for the new architecture
"""
import os
import logging
from app.services import RosterServiceFactory
from app.models.domain import ProcessingOptions

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_roster_processing():
    """Test the new roster processing architecture."""
    try:
        # Initialize the service factory
        factory = RosterServiceFactory()
        service = factory.create_service()
        
        # Set up processing options
        options = ProcessingOptions(
            show_empty=True,
            show_core=True,
            dont_show_renown=True
        )
        
        # Test with an existing roster file
        roster_file = "c74743b4-3846-4d91-a10a-bc3e4d06570e.rosz"
        if os.path.exists(f"battlescribe/{roster_file}"):
            logger.info(f"Processing roster file: {roster_file}")
            result = service.process_roster_file(roster_file, options)
            
            logger.info(f"Processing completed successfully!")
            logger.info(f"Total stratagems found: {len(result.all_stratagems)}")
            logger.info(f"Phases processed: {len(result.phases)}")
            logger.info(f"Units processed: {len(result.units)}")
            
            return result
        else:
            logger.error(f"Roster file not found: {roster_file}")
            
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_roster_processing()