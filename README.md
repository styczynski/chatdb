# 🖥️💬 ChatDB

**ChatDB** *(pronounced "theworstideaeverdb")* is just incredibly stupid idea to convince ChatGPT instance using its API, that it's a key-value store and
use it as a database that is incredibly slow, makes mistakes and do not always repond using the same format, buuuut
<br />
[*at least it can write you a poem when summing up the values!*](www.google.com)

[📚 Please can read full Medium article here](www.google.com)

<p align="center">
<img alt="Chat DB screenshot" width="600px" src="https://github.com/styczynski/chatdb/blob/main/static/screenshot.png?raw=true" />
</p>

## How does it work?

1. We clone the repo: `git clone https://github.com/styczynski/chatdb.git`
2. We install dependencies: `poetry install`
3. Now we need to open the browser and navigate to https://chat.openai.com/chat and log in or sign up
4. We need to open console with F12
5. Open Application tab > Cookies
6. Copy the value for `__Secure-next-auth.session-token` and paste that into `OpenAPIAuth(session_token="YOUR SESSION TOKEN")` inside `demo.py`
7. Now the last step is to execute `poetry run python3 demo.py`

![Chrome token](https://github.com/styczynski/chatdb/blob/main/static/token.png?raw=true)
