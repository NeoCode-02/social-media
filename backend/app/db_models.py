"""Aggregator that imports every module's ORM models.

Alembic's env.py imports this so ``Base.metadata`` is fully populated for
autogenerate. Add new model modules here as milestones land, e.g.::

    from app.modules.users import models as user_models  # noqa: F401
    from app.modules.chats import models as chat_models   # noqa: F401
"""

from app.modules.chats import models as chat_models  # noqa: F401
from app.modules.follows import models as follow_models  # noqa: F401
from app.modules.messages import models as message_models  # noqa: F401
from app.modules.posts import models as post_models  # noqa: F401
from app.modules.users import models as user_models  # noqa: F401
