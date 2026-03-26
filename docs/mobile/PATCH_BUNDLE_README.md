# Bentley Mobile Patch Bundle

This bundle is a starter implementation for the Bentley mobile monitoring flow.

## Included
- `app/api/routes/mobile.py`
- `app/templates/mobile/`
- `app/static/css/mobile.css`
- `app/static/js/mobile.js`
- `patches/0001-mobile-module.patch`

## Apply order
1. Copy the new files into the active repo.
2. Update `app/main.py` to include the mobile router.
3. Update `app/templates/base.html` to expose the new `Mobile Ops` nav item.
4. Update `smoke-test.sh` with the new endpoints.
5. Run the application and verify the routes.

## Notes
- `/mobile/admin` and `/api/mobile/admin-summary` should remain admin-protected.
- POST actions in `mobile.py` are intentionally lightweight and can be replaced with persistent models later.
- The monitor discovery action is a stub that acknowledges intent without inventing a new database model.
- The integration marketplace reuses the existing integration catalog and groups items with a mobile-specific mapping.
