"""
File Upload Service for Tenant Logo Management.

Handles file validation, storage, and retrieval for tenant logos.
"""

import os
import shutil
from pathlib import Path
from typing import Optional
from fastapi import UploadFile


class FileUploadError(Exception):
    """Custom exception for file upload errors."""
    pass


class FileUploadService:
    """
    File Upload Service for managing tenant logos.

    Attributes:
        upload_dir: Directory path for storing uploaded files
        allowed_extensions: Tuple of allowed file extensions
        allowed_mime_types: Tuple of allowed MIME types
        max_file_size: Maximum file size in bytes (default: 2MB)
    """

    # Allowed image extensions
    ALLOWED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.svg')

    # Allowed MIME types
    ALLOWED_MIME_TYPES = (
        'image/png',
        'image/jpeg',
        'image/svg+xml'
    )

    # Maximum file size: 2MB
    MAX_FILE_SIZE = 2 * 1024 * 1024

    def __init__(self, upload_dir: Optional[Path] = None):
        """
        Initialize File Upload Service.

        Args:
            upload_dir: Custom upload directory path.
                       Defaults to uploads/logos
        """
        if upload_dir is None:
            # Get the project root directory
            base_dir = Path(__file__).resolve().parent.parent
            upload_dir = base_dir / "uploads" / "logos"

        self.upload_dir = upload_dir

        # Create upload directory if it doesn't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def validate_file(self, file: UploadFile) -> None:
        """
        Validate uploaded file.

        Args:
            file: Uploaded file to validate

        Raises:
            FileUploadError: If file validation fails
        """
        # Check if file has a filename
        if not file.filename:
            raise FileUploadError("No filename provided")

        # Check file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            allowed = ', '.join(self.ALLOWED_EXTENSIONS)
            raise FileUploadError(
                f"Invalid file extension. Allowed: {allowed}"
            )

        # Check MIME type
        if file.content_type not in self.ALLOWED_MIME_TYPES:
            raise FileUploadError(
                "Invalid file type. Allowed: PNG, JPG, JPEG, SVG"
            )

        # Check file size
        file.file.seek(0, 2)  # Seek to end of file
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        if file_size > self.MAX_FILE_SIZE:
            max_size_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            raise FileUploadError(
                f"File size exceeds maximum allowed size of {max_size_mb}MB"
            )

    def save_logo(self, tenant_id: str, file: UploadFile) -> str:
        """
        Save tenant logo file.

        Args:
            tenant_id: Tenant ID
            file: Uploaded file

        Returns:
            Relative path to saved file

        Raises:
            FileUploadError: If file save fails
        """
        try:
            # Validate file
            self.validate_file(file)

            # Generate filename: tenant_id + original extension
            file_ext = os.path.splitext(file.filename)[1].lower()
            filename = f"{tenant_id}{file_ext}"
            file_path = self.upload_dir / filename

            # Delete old logo if exists
            self.delete_logo(tenant_id)

            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Return relative path (from project root)
            return f"uploads/logos/{filename}"

        except FileUploadError:
            raise
        except Exception as e:
            raise FileUploadError(f"Failed to save file: {str(e)}")

    def delete_logo(self, tenant_id: str) -> None:
        """
        Delete tenant logo files (all extensions).

        Args:
            tenant_id: Tenant ID
        """
        for ext in self.ALLOWED_EXTENSIONS:
            file_path = self.upload_dir / f"{tenant_id}{ext}"
            if file_path.exists():
                file_path.unlink()

    def get_logo_path(self, logo_url: Optional[str]) -> Optional[Path]:
        """
        Get absolute path to logo file.

        Args:
            logo_url: Relative logo URL from database

        Returns:
            Absolute path to logo file, or None if not found
        """
        if not logo_url:
            return None

        # Get project root
        base_dir = Path(__file__).resolve().parent.parent
        logo_path = base_dir / logo_url

        if logo_path.exists():
            return logo_path

        return None


# Create singleton instance
_file_upload_service: Optional[FileUploadService] = None


def get_file_upload_service() -> FileUploadService:
    """
    Get or create File Upload Service singleton instance.

    Returns:
        FileUploadService instance
    """
    global _file_upload_service
    if _file_upload_service is None:
        _file_upload_service = FileUploadService()
    return _file_upload_service
