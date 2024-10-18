import os
from git import Repo
import datetime as dt
tgl = dt.datetime.now().strftime("%y%m%d_%H%M%S")
os.chdir('/content/training')

full_local_path = "/content/training"

repo = Repo(full_local_path)
repo.git.add("-A")
repo.index.commit("user_fakes")

origin = repo.remote(name="origin")
origin.push()

os.chdir('/content')
