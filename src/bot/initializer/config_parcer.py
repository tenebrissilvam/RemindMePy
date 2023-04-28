import configparser
from dataclasses import dataclass  # for convenient class creation


@dataclass
class Bot:
    TOKEN: str
    DATABASE_PATH: str


@dataclass
class Config:
    bot: Bot


def load_config(file_path: str) -> Config:
    config = configparser.ConfigParser()
    config.read(file_path)

    bot = config['bot']
    return Config(bot=Bot(TOKEN=bot['TOKEN'], DATABASE_PATH=bot['DATABASE_PATH']))
