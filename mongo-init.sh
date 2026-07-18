#!/bin/bash
# Este script roda automaticamente na primeira vez que o container MongoDB sobe.
# Importa todas as colecoes do banco prontu_db a partir dos arquivos JSON.

echo ">>> Importando colecoes do prontu_db..."

mongoimport --db prontu_db --collection especialidades --file /docker-entrypoint-initdb.d/json/especialidades.json --jsonArray
mongoimport --db prontu_db --collection atendimentos   --file /docker-entrypoint-initdb.d/json/atendimentos.json   --jsonArray
mongoimport --db prontu_db --collection prescricoes    --file /docker-entrypoint-initdb.d/json/prescricoes.json    --jsonArray
mongoimport --db prontu_db --collection usuarios       --file /docker-entrypoint-initdb.d/json/usuarios.json       --jsonArray

echo ">>> Importacao concluida!"
