
[![Sainou.AI Demo](https://img.youtube.com/vi/jBtUBju_SrE/0.jpg)](https://www.youtube.com/watch?v=jBtUBju_SrE)

## Project Name: Sainou.AI

>_The Japanese word 'sainou' (才の) refers to a unique combination of innate talent, skill, and artistry – a natural aptitude that goes beyond mere ability.  I am leveraging this concept to reimagine the recruitment proces for employers and candidates._

**Elevator Pitch:** For the Google ADK Hackathon, I'm building a Multi-Agentic Hiring Workflow to streamline the recruitment process, reducing time and cost for both companies and candidates while fostering a more engaging and transparent experience.

## DevPost Hackathon
[Project Page](https://devpost.com/software/xxx-m05ywz)
[Blog Post](https://vikrampant.com/blog/my-week-long-journey-with-google-agent-development-kit-adk-for-a-hackathon-entry/)

## Running This Yourself

### ENV variables
You will need to configure your environment variables within the .env file.  [Google ADK docs](https://google.github.io/adk-docs/get-started/quickstart/#set-up-the-model)

### SQLite Databases
First there are two local SQLite databases that get created, the session state is automatically created by Google's ADK.  The second is the application database and that requires you running src/models/create.py.

### Deploy to Cloud Run or local Docker
The cloudbuild.yaml file supports deployment to a Cloud Run service named 'adk-hackathon'.
The DOCKERFILE can support you installing locally if needed.

Test Data is available data/test_data.txt