from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from pathlib import Path
from typing_extensions import Literal


HostingType = Literal['github', 'forgejo']


@dataclass
class PullRequest:
	body: str
	changed_files: int
	closed_at: Optional[datetime]
	created_at: datetime
	draft: bool
	repo_url: str
	pr_url: str
	labels: List[str]
	merge_commit_sha: Optional[str]
	merged: bool
	merged_at: Optional[datetime]
	number: int
	state: str
	title: str
	updated_at: datetime
	commits: List[str]
	hosting: HostingType
	org_id: str
	repo_id: str
	files_dir: Path
	author_username: str = ''
	author_name: str = ''
	files: List[Path] = field(default_factory=list)