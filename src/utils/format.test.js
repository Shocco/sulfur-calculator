import { test } from 'node:test'
import assert from 'node:assert/strict'
import { formatChange } from './format.js'

test('a fractional change keeps its decimals', () => {
  assert.equal(formatChange(-0.1), '-0.1')
  assert.equal(formatChange(0.15), '+0.15')
  assert.equal(formatChange(-2.55), '-2.55')
})

test('a whole-number change has no decimals', () => {
  assert.equal(formatChange(750), '+750')
  assert.equal(formatChange(-48), '-48')
})

test('floating point noise is rounded away', () => {
  assert.equal(formatChange(0.1 + 0.2), '+0.3')
})

test('a percentage-point change is shown as a percent', () => {
  assert.equal(formatChange(0.3, true), '+30%')
  assert.equal(formatChange(-0.05, true), '-5%')
})
