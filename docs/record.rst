Record and Evaluate New Data
============================

The `hwrt` toolkit contains a script `record.py` that allows a client to record
and evaluate. The script uses the current working directory as the recognition
system. That means it uses the same preprocessing queue, the same features and
the latest model file of that folder. The script gets this information by
examining the `info.yml`.