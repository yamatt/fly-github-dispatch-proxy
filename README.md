# GitHub Dispatch Proxy

I wanted to trigger runs of GitHub Workflows from another service, but I didn't want to give that service a Fine Grained Token that had write access to the repo.

This proxy makes calling those repos safer by calling your own trusted source with controller access.

This service is designed to be small and fast.

## Environment Variables

You need to provide these environment variables for this service to run.

* `GITHUB_PAT`: This needs `content:read`, `actions:read-write` and comes with meta-data.
* `TRIGGER_AUTH_TOKEN`: This is some secret you define that the calling service uses to authenticate

## Running

You need uv installed.

Then run:

```sh
GITHUB_PAT=<GITHUB_PAT> TRIGGER_AUTH_TOKEN=<TRIGGER_AUTH_TOKEN> uv run granian --interface asgi main:app --port 8080
```

## Calling

```sh
curl -XPOST -H "Authorization: Bearer <TRIGGER_AUTH_TOKEN>" https://gh-dispatch-proxy-mc.fly.dev/trigger/<github owner>/<github repo>/<workflow file name>
```
