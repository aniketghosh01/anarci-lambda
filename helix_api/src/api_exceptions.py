from fastapi import HTTPException, status


not_found_exception = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Could not find requested resource.")
