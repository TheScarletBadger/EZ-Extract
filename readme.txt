Simple FastAPI application that accepts files via a post request.

Files are temporarily stored to the filesystem and a job ID is returned in the response body.

Text and tabular data are then extracted using pdf plumber and sent to an LLM for structured extraction.

Instructor library is used to constrain the llms responses to a defined schema.

Structured output can then be queried using a get request using the job ID.

LM studio used as LLM backend
SQLite file used as db
