# Contributing Providers

This guide explains how to add new streaming services to this repository. Right now providers are represented as static assets (logos) and optional template entries. There is no `provider_config.json` or automated deep-link schema in this codebase.

## Where provider assets live

Provider logos are stored in:

```
templates/images/
```

Existing examples include `netflix.png`, `disney+.png`, `movistar+.png`, and `hbo_max.png`.

## Add a new provider

1. Add the logo file to `templates/images/`.
2. Use a consistent filename:
   - Lowercase
   - Use underscores for spaces
   - Keep the original brand name if it includes `+` (e.g. `disney+.png`)
3. Wire the logo into the UI by updating the appropriate template. At the moment, there is no shared provider list or component, so you will need to add the `<img>` tag where the provider list is rendered (or create that section if it does not exist yet).

If you decide to make providers dynamic, update the corresponding view in `StreamSync/views.py` to pass a provider list in the context and render it in the template.

## Verification

There are no provider-specific automated tests. After updating templates:

```bash
python manage.py test
python manage.py runserver
```

Then load the relevant page in the browser and confirm the new logo renders correctly.

## Logo guidelines

- Use PNG with a transparent background (matching the current assets).
- Keep the logo legible at small sizes (24–32px height is a good target).
- Avoid adding large files; optimize the image before committing.
