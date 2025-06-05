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
    STEP1 = 'step1'  # step 1 in the training process
    STEP2 = 'step2'  # step 2 in the training process
    STEP3 = 'step3'  # step 3 in the training process


ENV_TYPE_TO_VARIANTS: Dict[EnvType, List[EnvVariant]] = {
    EnvType.BASIC_FLAPPY: [EnvVariant.MAIN],
    EnvType.ENEMY_CLOUDSKIMMER: [EnvVariant.MAIN, EnvVariant.STEP1, EnvVariant.STEP2, EnvVariant.STEP3],
    EnvType.ADVANCED_FLAPPY: [EnvVariant.MAIN]
}
