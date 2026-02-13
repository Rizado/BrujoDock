from .plugin import ThumbnailPreviewPlugin

def load(dock):
    return ThumbnailPreviewPlugin(dock)
