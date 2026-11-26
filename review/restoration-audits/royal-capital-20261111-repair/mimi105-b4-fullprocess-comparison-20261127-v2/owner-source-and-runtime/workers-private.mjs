// Existing D1 shim only; database files belong exclusively to the new A kit.
import {createLocalD1} from '../../stella-local-deployment-3394828/d1-local.mjs';
import {pathToFileURL} from 'node:url';
import {resolve} from 'node:path';
const database=process.env.STELLA_PRIVATE_OUTPUT
  ?pathToFileURL(resolve(process.env.STELLA_PRIVATE_OUTPUT,'local-runtime.sqlite'))
  :new URL('frozen/local-preparation.sqlite',import.meta.url);
export const env={DB:createLocalD1(database)};
