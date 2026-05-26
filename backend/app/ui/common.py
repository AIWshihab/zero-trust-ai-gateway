# Shared design-system assets are now in static files:
#   backend/app/static/css/common.css      — CYBER_UI_CSS
#   backend/app/static/js/tailwind-config.js
#   backend/app/static/js/common.js        — CYBER_UI_JS injectShell IIFE
#
# These constants are kept as empty strings for backward-compat with any
# import that wasn't yet updated, but they carry no content.
CYBER_UI_CSS = ""
CYBER_UI_JS  = ""
