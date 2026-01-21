#!/bin/bash
DOMAIN=$(env | grep REPLIT_DEV_DOMAIN | cut -d= -f2)
SLUG=$(env | grep REPL_SLUG | cut -d= -f2)
OWNER=$(env | grep REPL_OWNER | cut -d= -f2)

if [ -z "$DOMAIN" ]; then
  DOMAIN="$SLUG.$OWNER.replit.dev"
fi

PROD_DOMAIN="$SLUG.$OWNER.replit.app"

echo "Dev URL: https://$DOMAIN/dashboard"
echo "Prod URL: https://$PROD_DOMAIN/dashboard"
