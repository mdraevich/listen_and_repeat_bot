# TODO

1. poll_channels_module, handle FloodWaitError exception.
2. add feature to ignore specific questions from asking.
3. add feature to add user-defined answers for questions.
4. add feature to define different parsers for different channel.
5. add more unit tests before building; add unit tests after building.

### Create authentication file

1. Prepare `./secrets` directory if it doesn't exist:
```shell
# in the project root directory

mkdir -p secrets
```


2. Prepare environment file with required parameters:
```shell
# in the project root directory

cd session_handler/
echo "API_ID=$API_ID" > .env
echo "API_HASH=$API_HASH" >> .env
echo "SESSION_NAME=$SESSION_NAME" >> .env
```

3. Follow the authentication process to create a session file:
```shell
# in the project root directory

cd session_handler/
pipenv install
pipenv run python3 main.py
```