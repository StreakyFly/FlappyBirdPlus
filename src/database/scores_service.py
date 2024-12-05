from database import supabase

# TODO: store all player scores in a local text file, just in case they aren't connected to the internet


# TODO: call this when the game ends
def add_score(username: str, score: int):
    response = (
        supabase.table('Scores')
        .insert({
            'username': username,
            'score': score,
        })
        .execute()
    )

    # TODO: get rid of these print statements
    if response and response.data:
        print(f"Score for '{username}' added successfully!")
    else:
        print(f"Error adding score for '{username}'.")
