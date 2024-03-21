from enum import Enum


class EnvType(Enum):
    BASIC_FLAPPY = 'basic_flappy'  # env for training only the basic flappy bird
    ENEMY_CLOUDSKIMMER = 'enemy_cloudskimmer'  # env for training the enemy cloudskimmer with basic flappy bird
    ENEMY_AEROTHIEF = 'enemy_aerothief'  # env for training the enemy aerothief with basic flappy bird
    ADVANCED_FLAPPY = 'advanced_flappy'  # env for training the advanced flappy bird with both enemy agents
