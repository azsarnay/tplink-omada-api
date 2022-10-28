# What's this?

A basic Python client for calling the TP-Link Omada controller API.

## Supported features

Not many:
* Automatic Login/Re-login
* List Devices (APs, Gateways and Switches)
* Basic device information
* Port status and PoE configuraton for Switches (<-- What I actually needed)

## Future

The available API surface is quite large. More of this could be exposed in the future.
There is an undocumented Websocket API which could potentially be used to get a stream of updates. However,
I'm not sure how fully featured this subscription channel is on the controller. It seems to be rarely used,
so probably doesn't include client connect/disconnect notifications.

## Contributing

There is a VS Code development container, which sets up all of the requirements for running the package.

## License

MIT Open Source license.
