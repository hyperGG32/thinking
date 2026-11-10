from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.views import exception_handler
from rest_framework_simplejwt.exceptions import InvalidToken


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Конфлікт з поточним ресурсом"


def challenges_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    if response.status_code == 404:
        response.data = {
            "error": "Отакої! Шукали і тут і там, не змогли знайти... "
                     "Спробуйте пошук з іншими параметрами!",
            "fields": None
        }
    elif isinstance(exc, ValidationError):
        fields = (
            response.data
            if isinstance(response.data, dict)
            else {"non_field_errors": response.data}
        )
        response.data = {
            "error": f"Невалідні дані, виправте поля '"
                     f"{', '.join(fields)}', "
                     f"і спробуйте знову!",
            "fields": fields,
        }
    elif isinstance(exc, InvalidToken):
        response.data = {"error": "Токен неправильний, спробуйте його оновити",
                         "fields":
                             None}
    else:
        response.data = {"error": response.data.get("detail"), "fields": None}

    return response
