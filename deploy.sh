#!/bin/bash
# deploy.sh
# Развертывание Hello Park Analytics на прод: https://party.hello-park.io/analytics/

MEGA_ANALYTICS_DIR="/Users/dima/Desktop/DR-construct-Mega/analytics"

if [ ! -d "$MEGA_ANALYTICS_DIR" ]; then
  echo "Ошибка: директория $MEGA_ANALYTICS_DIR не найдена!"
  exit 1
fi

echo "=== 1. Синхронизируем файлы в $MEGA_ANALYTICS_DIR ==="
cp -r backend "$MEGA_ANALYTICS_DIR/"
cp -r frontend "$MEGA_ANALYTICS_DIR/"
cp requirements.txt "$MEGA_ANALYTICS_DIR/"

echo "=== 2. Коммитим и пушим в репозиторий mega для автодеплоя на party.hello-park.io ==="
cd "/Users/dima/Desktop/DR-construct-Mega"
git add analytics/
git commit -m "feat(analytics): update analytics dashboard"
git push origin main

echo ""
echo "=== Деплой запущен! ==="
echo "Через 2-3 минуты изменения применятся на: https://party.hello-park.io/analytics/"
