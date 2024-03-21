from enum import Enum


class Mode(Enum):
    PLAY = 'play'
    TEST_ENV = 'test-env'
    TRAIN = 'train'
    CONTINUE_TRAINING = 'continue-training'
    RUN_MODEL = 'run-model'
    EVALUATE_MODEL = 'evaluate-model'
