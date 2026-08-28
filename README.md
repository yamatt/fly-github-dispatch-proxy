# GitHub Dispatch Proxy

I wanted to trigger runs of GitHub Workflows from another service, but I didn't want to give that service a Fine Grained Token that had write access to the repo.

This proxy makes calling those repos safer by calling your own trusted source with controller access.

This service is designed to be small and fast.

## Environment Variables

You need to provide these environment variables for this service to run.

* `GITHUB_PAT`: This needs `content:read`, `actions:read-write` and comes with meta-data.
* `TRIGGER_AUTH_TOKEN`: This is some secret you define that the calling service uses to authenticate
