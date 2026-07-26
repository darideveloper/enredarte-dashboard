from utils.admin_icons import build_sidebar_icon_map


def user_palette(request):
    return {
        "user_palette_css": "",
        "sidebar_icons": build_sidebar_icon_map(),
    }
