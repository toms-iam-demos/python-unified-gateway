import test from 'node:test';
import assert from 'node:assert/strict';
import {hasWorkflowSession} from '../deploy/clm/workflow-session.mjs';
const valid = {expectedURL:'https://clm.example.test/clm/workflow?aid=demo',actualURL:'https://clm.example.test/clm/workflow?aid=demo',title:'Workflows - Docusign CLM',newWorkflowVisible:true,loginPromptVisible:false};
test('a loaded native workflow view proves browser readiness',()=>assert.equal(hasWorkflowSession(valid),true));
for (const [name, change] of Object.entries({
  'other account':{actualURL:'https://clm.example.test/clm/workflow?aid=other'},
  'ambiguous account':{actualURL:'https://clm.example.test/clm/workflow?aid=demo&aid=other'},
  'missing account':{actualURL:'https://clm.example.test/clm/workflow'},
  'login page':{actualURL:'https://clm.example.test/login?aid=demo'},
  'other origin':{actualURL:'https://attacker.example.test/clm/workflow?aid=demo'},
  'lookalike origin':{actualURL:'https://clm.example.test.attacker.invalid/clm/workflow?aid=demo'},
  'insecure origin':{actualURL:'http://clm.example.test/clm/workflow?aid=demo'},
  'wrong title':{title:'Sign in'},
  'hidden native control':{newWorkflowVisible:false},
  'login prompt':{loginPromptVisible:true},
  'missing login observation':{loginPromptVisible:undefined},
  'invalid URL':{actualURL:'invalid'}
})) test(name+' fails closed',()=>assert.equal(hasWorkflowSession({...valid,...change}),false));
