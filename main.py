from mode_manager import validate_mode, execute_mode, ModeExecutor  # noqa: F401  # ModeExecutor must be imported for profiling to work


def main():
    validate_mode()
    execute_mode()


if __name__ == "__main__":
    main()
