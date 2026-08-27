"""检查两个数据库中的默认模板状态"""
import asyncio, sys, os
from pathlib import Path

# 检查两个可能的数据库路径
backend_dir = Path(r"d:\唐宏\实验室\备课助手\backend")
for cwd in [Path(r"d:\唐宏\实验室\备课助手\backend"), Path(r"d:\唐宏\实验室\备课助手")]:
    os.chdir(str(cwd))
    sys.path.insert(0, str(backend_dir))
    # 重新加载配置
    import importlib
    from app import config
    importlib.reload(config)
    from app.storage.db import AsyncSessionLocal, LessonTemplateORM
    from sqlalchemy import select
    db_path = config.settings.db_path
    print(f"\nCWD: {cwd}")
    print(f"DB path: {db_path}")
    print(f"DB exists: {db_path.exists()}")

    async def check():
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(LessonTemplateORM))
            tpls = result.scalars().all()
            print(f"Total templates: {len(tpls)}")
            for t in tpls:
                print(f"  id={t.id} name={t.name} is_default={t.is_default} course_id={t.course_id}")
    asyncio.run(check())