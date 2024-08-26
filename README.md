# FastAPI
- Установить зависимости
```bash
pip install -r requirements.txt
```
- Запустите при помощи start.sh. Он запустит миграции а затем приложение
```bash
chmod 755 start.sh
sh start.sh
```

- Запуск клиента чтобы протестировать работу сокетов
```bash
python src/socket_client/client.py
```

## Регистрация
Для регистрации, перейдите по ссылке `http://localhost:8081/docs#/default/register_register__post`
и введите данные для регистрации, после чего в консоли отобразится
`token='...'`
Скопируйте токен и введите его в апи [верификации](http://localhost:8081/docs#/default/verify_verify__get). Теперь пользователь считается активным.

## Авторизация
Для авторизации введите email и password в swagger Authorize.

## Публичные чаты
Существуют публичные чаты в которых пользователи могут создавать комнаты.
По умолчанию к каждому чату автоматически создается комната.
Создание чата происходит по ссылке [chat](http://localhost:8081/docs#/default/create_public_chat_chat__post)
В ответ приходит `chat_id` и `conversation_id`.
Для того чтобы создать комнату, сначала необходимо присоединиться к чату
по ссылке [`/chat/{chat_id}/enjoy`](http://localhost:8081/docs#/default/enjoy_public_chat_chat__chat_id__enjoy_post) и указать `chat_id`.
Теперь можно создавать дополнительные комнаты для общения по ссылке
[`/chat/{chat_id}/create_conversation`](http://localhost:8081/docs#/default/create_public_chat_conversation_chat__chat_id__create_conversation_post)

## Приватные чаты
Помимо публичных чатов существуют приватные чаты для двух пользователей.
Для создания приватного чата перейдите в [`/private_chat`](http://localhost:8081/docs#/default/create_private_chat_private_chat_post) и укажите email
собеседника.

## Общение при помощи сокетов.
Общение пользователей происходит комнатах. Для начала общения необходимо указать
`token` клиента а также `conversation_id` комнаты.
Токен можно узнать при авторизации через `/login/` или в curl запросе в
swagger после авторизации.