# drone-matrixchat-notify

A [drone.io] [plugin] to send notifications to Matrix chat rooms from
CI pipeline steps.

Example pipeline configuration:

```yaml
kind: pipeline
type: docker
name: default

steps:
- name: build
  image: alpine
  commands:
  - ./build

- name: notify
  image: spotlightkid/drone-matrixchat-notify
  settings:
    homeserver: 'https://matrix.org'
    roomid: '!xxxxxx@matrix.org'
    userid: '@drone-bot@matrix.org'
    password:
      from_secret: drone-bot-pw
    template: '${DRONE_REPO} ${DRONE_COMMIT_SHA} ${DRONE_BUILD_STATUS}'
```

# Configuration settings

* `accesstoken`

    Access token to use for authentication instead of `password`. Either an
    access token or a password is required.

* `deviceid`

    Device ID to send with access token.

* `devicename`

    Device name to send with access token.

* `homeserver` *(default:* `https://matrix.org`*)*

    The Matrix homeserver URL.

* `markdown`

    If set to `yes`, `y`, `true` or `on`, the message resulting from template
    substtution is considered to be in Markdown format and will be rendered to
    HTML and sent as a formatted message with `org.matrix.custom.html` format.

* `password`

    Password to use for authenticating the user set with `userid`. Either a
    password or an access token is required.

* `roomid` *(required)*

    ID of matrix chat room to send messages to (ID, not alias).

* `template` *(default:* `${DRONE_BUILD_STATUS}`*)*

    The message template. Valid placeholders of the form `${PLACEHOLDER}` will
    be substituted with the values of the matching environment variables.

    See this [reference] for environment variables available drone.io in CI
    pipelines.

* `userid` *(required)*

    ID of user on homeserver to send message as (ID, not username).


[drone.io]: https://drone.io/
[plugin]: https://docs.drone.io/plugins/overview/
[reference]:  https://docs.drone.io/pipeline/environment/reference/
