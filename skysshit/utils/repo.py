from utils import default

version = "v1"
invite = "https://discord.gg/xebcjtG"
owners = default.get("config.json").owners


def is_owner(ctx):
    return ctx.author.id in owners
