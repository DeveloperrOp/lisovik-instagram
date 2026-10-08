#!/usr/bin/env bash
# Одна ланка ланцюга: 5 годин 40 хвилин опитує чергу кожні 8 хвилин.
#
# Ліміт GitHub у 6 годин діє на ОДИН job, а не на весь запуск. Тому
# publish.yml ставить пʼять таких ланок одну за одною: разом це майже
# доба, і одного старту на день досить. Раніше цикл був один, жив 5:45,
# а GitHub давав 2-3 старти на добу — між ними лишались дірки, і 08.10
# така дірка припала рівно на ранкове вікно 07:00-09:45.
set -u

END=$(( $(date +%s) + 5*3600 + 40*60 ))

while [ "$(date +%s)" -lt "$END" ]; do
  echo "--- $(TZ=Europe/Kyiv date '+%F %H:%M') Київ"

  # Статуси пише і цей цикл, і локальний планувальник власника. Без
  # підтягування вони розійдуться, і кадр піде у стрічку двічі.
  git pull --rebase -q origin master || true

  python src/publish.py || true

  git add content/manifest.json
  if ! git diff --staged --quiet; then
    git commit -q -m "queue: update publish status"
    git push -q || { git pull --rebase -q origin master; git push -q || true; }
  fi

  sleep 480
done

echo "ланка відпрацювала, наступна підхоплює"
