// Run with: node frontend/tests/importer.test.mjs
import assert from "node:assert/strict";
import { parseQuestions } from "../js/importer.js";

// plain numbered list, headings and topics
let r = parseQuestions(`Part 1\nTopic: Hometown\n1. Where is your hometown?\n2) Do you like living there?\n\nPart 3\nTopic: Technology\n- How might technology change work?\n`);
assert.equal(r.items.length, 3);
assert.deepEqual(r.items.map((i) => [i.part, i.topic]), [[1, "Hometown"], [1, "Hometown"], [3, "Technology"]]);

// cue card with "You should say"
r = parseQuestions(`Part 2\nDescribe a website you find useful.\nYou should say:\n- what it is\n- how you found it\n- why it is useful\n\nDescribe a teacher you remember.\nYou should say:\nwho the teacher was\nwhat they taught`);
assert.equal(r.items.length, 2);
assert.equal(r.items[0].part, 2);
assert.deepEqual(r.items[0].cue_points, ["what it is", "how you found it", "why it is useful"]);
assert.equal(r.items[1].cue_points.length, 2);

// guessing and overriding the part
r = parseQuestions("Describe a place you like.\nDo you like cooking?");
assert.deepEqual(r.items.map((i) => i.part), [2, 1]);
assert.equal(r.assumedPart, 1);
assert.deepEqual(parseQuestions("Do you like cooking?", { defaultPart: 3 }).items.map((i) => i.part), [3]);

// duplicates and noise
assert.equal(parseQuestions("Do you like cooking?\ndo you like cooking?\nok").items.length, 1);

// JSON and CSV
r = parseQuestions(JSON.stringify([{ part: 1, topic: "Food", question: "What food do you enjoy?" }, { part: 2, text: "Describe a meal.", cues: "what|where" }]));
assert.equal(r.items.length, 2);
assert.deepEqual(r.items[1].cue_points, ["what", "where"]);
r = parseQuestions('part,topic,question\n1,Hobbies,"Do you have hobbies, or not?"\n3,Technology,How has technology changed life?');
assert.equal(r.items.length, 2);
assert.equal(r.items[0].text, "Do you have hobbies, or not?");
assert.equal(parseQuestions("").items.length, 0);
console.log("importer tests passed");
