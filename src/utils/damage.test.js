import { test } from 'node:test'
import assert from 'node:assert/strict'
import { totalDamage, formatTotalDamage, formatDamage } from './damage.js'

test('total damage is damage times projectiles', () => {
  assert.equal(totalDamage({ damage: 60, projectiles: 1 }), 60)
  assert.equal(totalDamage({ damage: 40, projectiles: 8 }), 320)
})

test('bonus damage per projectile is included in the total', () => {
  assert.equal(totalDamage({ damage: 40, projectiles: 8, bonus: 6.25 }), 370)
})

test('weapons that fire several shells per trigger pull multiply the total', () => {
  assert.equal(totalDamage({ damage: 40, projectiles: 8, shotsPerTrigger: 3 }), 960)
  assert.equal(totalDamage({ damage: 50, projectiles: 3, shotsPerTrigger: 3 }), 450)
})

test('a variable number of shells gives a range', () => {
  assert.deepEqual(totalDamage({ damage: 40, projectiles: 8, shotsPerTrigger: [1, 8] }), [320, 2560])
})

test('the total is rounded to two decimals', () => {
  assert.equal(totalDamage({ damage: 41.88, projectiles: 8 }), 335.04)
})

test('missing values fall back to a single projectile and no damage', () => {
  assert.equal(totalDamage({}), 0)
  assert.equal(totalDamage({ damage: 60 }), 60)
})

test('a total is formatted as a number or a range', () => {
  assert.equal(formatTotalDamage(960), '960')
  assert.equal(formatTotalDamage([320, 2560]), '320–2560')
})

test('damage is formatted with its projectile count and shells per trigger pull', () => {
  assert.equal(formatDamage(60, 1), '60')
  assert.equal(formatDamage(40, 8), '40x8')
  assert.equal(formatDamage(40, 8, 3), '40x8x3')
  assert.equal(formatDamage(40, 8, [1, 8]), '40x8 x1–8')
  assert.equal(formatDamage(50, 2.6), '50x3')
})
