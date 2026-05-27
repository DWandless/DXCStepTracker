"""
Challenge management module for DXC Step Tracker.
Handles challenge data loading, claim code generation, and validation.
"""

import json
import logging
import string
import random
import hashlib
from pathlib import Path


def get_all_challenges():
    """
    Load all challenges from the Challenges.json file.
    
    Returns:
        Dictionary of challenge data, or empty dict if file not found or invalid
    """
    try:
        base_dir = Path(__file__).resolve().parent.parent
        challenges_path = base_dir / ".streamlit" / "static" / "assets" / "Challenges.json"
        
        if not challenges_path.exists():
            error_msg = f"Challenges.json not found at: {challenges_path}"
            logging.error(error_msg)
            return []
        
        with open(challenges_path, "r") as f:
            challenges = json.load(f)
            return challenges
    except Exception as e:
        error_msg = f"Error loading challenges: {e}"
        logging.error(error_msg)
        return []


def get_all_existing_codes(challenges: list[dict]) -> set[str]:
    """
    Get all existing claim codes from all challenges.
    
    Args:
        challenges: List of challenge dicts containing "Codes" lists
        
    Returns:
        Set of all existing claim codes
    """
    existing_codes = set()
    for challenge in challenges:
        if "Codes" in challenge:
            existing_codes.update(challenge["Codes"])
    return existing_codes


def generate_claim_code(challenges: list[dict], AlreadyGenerated: set[str], length: int = 8, max_attempts: int = 10_000) -> str:
    """
    Generate a random alphanumeric claim code that is unique across all challenges.

    Args:
        challenges: List of challenge dicts containing "Codes" lists
        AlreadyGenerated: Set of codes that have already been generated
        length: Length of the claim code (default 8)
        max_attempts: Safety cap to prevent infinite loops

    Returns:
        A unique randomly generated claim code

    Raises:
        RuntimeError: If a unique code cannot be found within max_attempts
        ValueError: If length is invalid
    """
    if length < 4:
        raise ValueError("length should be at least 4")
    
    characters = string.ascii_uppercase + string.digits
    existing_codes = get_all_existing_codes(challenges)

    for _ in range(max_attempts):
        claim_code = ''.join(random.choice(characters) for _ in range(length))
        if claim_code not in existing_codes and claim_code not in AlreadyGenerated:
            AlreadyGenerated.add(claim_code)
            return claim_code

    raise RuntimeError("Unable to generate a unique claim code — increase length or max_attempts.")


def hash_claim_code(code: str) -> str:
    """
    Hash a claim code using SHA256 for secure storage.
    
    Args:
        code: The plain text claim code to hash
    
    Returns:
        The SHA256 hash of the code as a hexadecimal string
    """
    return hashlib.sha256(code.encode()).hexdigest()


def validate_claim_code(challenges: list[dict], code: str, challenge_id: str) -> bool:
    """
    Validate a claim code against a specific challenge by comparing hashes.
    
    Args:
        challenges: List of challenge dicts, each containing a "Codes" list
        code: The claim code to validate
        challenge_id: The ID of the specific challenge to validate against
    
    Returns:
        True if the code is valid for the specific challenge, False otherwise
    """
    code_hash = hash_claim_code(code)
    for challenge in challenges:
        if str(challenges[challenge]["id"]) == str(challenge_id):
            if code_hash in challenges[challenge]["Codes"]:
                return True
            return False
    return False


def save_claim_codes_to_file(challenge_title: str, hashed_codes: list[str]):
    """
    Save hashed claim codes to the Challenges.json file.
    
    Args:
        challenge_title: Title of the challenge to add codes to
        hashed_codes: List of hashed claim codes to add
    """
    try:
        base_dir = Path(__file__).resolve().parent.parent
        challenges_path = base_dir / ".streamlit" / "static" / "assets" / "Challenges.json"
        
        with open(challenges_path, "r") as f:
            challenges_data = json.load(f)
        
        # Add hashed codes to the selected challenge
        for challenge_key in challenges_data:
            if challenges_data[challenge_key]["title"] == challenge_title:
                challenges_data[challenge_key]["Codes"].extend(hashed_codes)
                break
        
        # Write back to file
        with open(challenges_path, "w") as f:
            json.dump(challenges_data, f, indent=4)
    except Exception as e:
        logging.error(f"Error saving claim codes: {e}")
