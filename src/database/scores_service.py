from .database import supabase
import requests


def submit_score(username: str, score: int):
    try:
        response = (
            supabase.table('Scores')
            .insert({
                'username': username,
                'score': score,
            })
            .execute()
        )
    except requests.ConnectionError:
        print("No internet connection. Score not submitted.")
        return

    # TODO: get rid of these print statements
    if response and response.data:
        print(f"Score for '{username}' added successfully!")
    else:
        print(f"Error adding score for '{username}'.")


def get_scores(count: int = 100):
    try:
        response = (
            supabase.table('Scores')
            .select('username, score, timestamp')
            .order('score', desc=True)
            .limit(count)
            .execute()
        )
    except requests.ConnectionError:
        print("No internet connection. Scores not fetched.")
        return [{'score': '---', 'timestamp': '---'}]

    if response and response.data:
        return response.data
    else:
        print("Error fetching scores.")
        return [{'score': '---', 'timestamp': '---'}]
