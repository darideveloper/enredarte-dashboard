from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile


def get_media_url(object_or_url: object) -> str:
    url_str = ""
    if type(object_or_url) is str:
        url_str = object_or_url
    else:
        url_str = object_or_url.url

    if "s3.amazonaws.com" not in url_str and "digitaloceanspaces" not in url_str:
        return f"{settings.HOST}{url_str}"
    return url_str


def get_test_image(image_name: str = "test.webp") -> SimpleUploadedFile:
    image_path = settings.BASE_DIR / "media" / image_name
    image_file = SimpleUploadedFile(
        name=image_name,
        content=open(image_path, "rb").read(),
        content_type="image/webp",
    )
    return image_file
