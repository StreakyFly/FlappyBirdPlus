from enum import Enum
from typing import Dict, List


class EnvType(Enum):
    BASIC_FLAPPY = 'basic_flappy'  # env for training basic flappy bird
    ENEMY_CLOUDSKIMMER = 'enemy_cloudskimmer'  # env for training enemy cloudskimmer with basic flappy bird
    ADVANCED_FLAPPY = 'advanced_flappy'  # env for training advanced flappy bird with all enemy agents


class EnvVariant(Enum):
    """
    Defines possible variants for each EnvType.

    The MAIN variant represents the default, full environment.
    Additional variants may be defined for simplified or specialized training,
    but they are optional and only included when needed.
    """
    MAIN = 'main'  # the default, full environment
    STATIC = 'static'  # a simplified version of the environment, where entities are mostly static


ENV_TYPE_TO_VARIANTS: Dict[EnvType, List[EnvVariant]] = {
    EnvType.BASIC_FLAPPY: [EnvVariant.MAIN],
    EnvType.ENEMY_CLOUDSKIMMER: [EnvVariant.MAIN, EnvVariant.STATIC],
    EnvType.ADVANCED_FLAPPY: [EnvVariant.MAIN]
}
