KIPAC TeaBot
============

Copyright (c) 2017-2021 [Yao-Yuan Mao](https://yymao.github.io)

KIPAC TeaBot is an automatic system which browses through new arXiv astro-ph papers everyday and sends personal suggestions to subscribers. It also sends discussion suggestions to Tea orangizers, and discovers new papers that are authored by KIPAC members.

Currently this system is open to KIPAC members only. **If you are a member of KIPAC and want to become a subscriber, please ask your fellow KIPAC members for instructions.**

Current subscribers can [create an issue](https://github.com/yymao/kipac-teabot/issues/new) to report a bug or to request a feature (but there is no guarantee that they will be implemented).

There isn't a concrete plan to expand this service, or to make the system easy to install. However, if you are interested in this, please feel free to reach out to me. 

## Deploy

Unfortunataly I didn't spend much effort to make it easy to deploy the TeaBot. If you wish to deploy it somewhere else, you will be mostly on your own! 
But here's some basic steps!

1. You need to have a SMTP server and being able to run cron job. 
2. You need to create a `secrets.py` to store some path/password information. See below for an example:
    ```python
    """
    secrets.py
    """

    keypass = 'a_random_string_to_be_used_as_salt"
    find_someone_pass = 'a_passphrase'
    member_list_url = 'URL to a CSV file'
    member_list_path = 'path/to/member/list/file
    db_path = 'path/to/a/dir/to/store/database'
    collection_weight_path =  'path/to/a/file/that/stores/model/weight'
    discovery_archive = 'path/to/a/dir/to/store/archive'
    update_prefs_path = 'path/to/a/file/that/stores/user/prefs'
    discovery_team = ['Organizer A <a@email.com>', 'Organizer B <b@email.com>']
    tealeaks_team = ['Organizer A <a@email.com>', 'Organizer B <b@email.com>']
    ```
3. Config your SMTP server [here](https://github.com/yymao/kipac-teabot/blob/master/email_server/__init__.py#L24).
4. The member CSV file should contain the following column names: `name`, `nickname`, `arxivname`, `email`, `active`, `is_kipac`
5. Set up cron jobs to run the following daily:
    ```bash
    ./members.py pull   # pull the CSV file (member_list_url) to local (member_list_path)
    ./teabot.py	        # the main routine for TeaBot to send out recommandation emails
    ./discovery.py      # discover any new papers authored by your members
    ./update_models.py  # update the prediction model for each member
    ```
    
