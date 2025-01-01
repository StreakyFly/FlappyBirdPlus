from .database import supabase

# TODO: store all player scores in a local text file, just in case they aren't connected to the internet


# TODO: call this when the game ends
def submit_score(username: str, score: int):
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


def get_scores(count: int = 100):
    response = (
        supabase.table('Scores')
        .select('score, timestamp')
        .order('score', desc=True)
        .limit(count)
        .execute()
    )

    if response and response.data:
        return response.data
    else:
        print("Error fetching scores.")
        return [{'score': '---', 'timestamp': '---'}]
