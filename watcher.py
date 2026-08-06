from watcher_core import clear_screen, run_full, export_ids, Color

if __name__ == "__main__":

    clear_screen()

    while True:

        print(f"{Color.CYAN}{Color.BOLD}" + "=" * 45)
        print("         🎬 YOUTUBE VIDEO INSPECTOR")
        print("=" * 45 + f"{Color.RESET}")
        print(f" {Color.GREEN}1.{Color.RESET} Scan Playlists & Check Changes")
        print(f" {Color.YELLOW}2.{Color.RESET} Export All IDs to Text File")
        print(f" {Color.RED}3.{Color.RESET} Exit")
        print(f"{Color.CYAN}" + "-" * 45 + f"{Color.RESET}")

        choice = input(
            f"{Color.BOLD}Enter your choice (1-3): {Color.RESET}"
        ).strip()

        if choice == "1":

            run_full()

            input(
                f"\n{Color.CYAN}Press Enter to return to main menu...{Color.RESET}"
            )

            clear_screen()

        elif choice == "2":

            export_ids()

            input(
                f"\n{Color.CYAN}Press Enter to return to main menu...{Color.RESET}"
            )

            clear_screen()

        elif choice == "3":

            print(
                f"\n{Color.GREEN}"
                "Exiting... Goodbye! 👋"
                f"{Color.RESET}"
            )

            break

        else:

            print(
                f"{Color.RED}\n"
                "✖ Invalid choice. Please try again.\n"
                f"{Color.RESET}"
            )