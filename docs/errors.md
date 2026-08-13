# Errors

The client normalizes relevant Home Assistant and transport failures into
stable integration errors.

| Condition | Error code |
|---|---|
| HTTP 401 | `unauthorized` |
| HTTP 404 | `not_found` |
| entity state `unavailable` | `unavailable` |
| HTTP transport failure | `connection_error` |
| invalid or unexpected response | `response_error` |

Configuration failures use `configuration_error`.

The access token is never included in these error messages.
