import { test } from 'node:test'
import assert from 'node:assert/strict'
import { refreshItem, refreshItems, refreshAttachments, refreshBuild } from './builds.js'

// Current data, as loaded from public/data/*.json
const weapon = { id: 'Weapon_Test', name: 'Test SMG', baseStats: { Damage: 60, Weight: 12 } }
const oil = { id: 'Shaved_Clip_Oil', name: 'Shaved Clip Oil', modifiers: [{ attribute: 'ReloadSpeed', modType: 200, value: 1 }] }
const otherOil = { id: 'Action_Oil', name: 'Action Oil', modifiers: [] }
const scroll = { id: 'Scroll_of_Light', name: 'Scroll of Light', modifiers: [{ attribute: 'RPM', modType: 200, value: -0.25 }] }
const scope = { id: 'Sniper_Scope', name: 'Sniper Scope', type: 'sight', modifiers: { ADSCritChance: { value: 0.3, type: 'percent' } } }
const data = {
  weapons: [weapon],
  oils: [oil, otherOil],
  scrolls: [scroll],
  attachmentsByType: { muzzle: [], sight: [scope], laser: [], chamber: [], chisel: [], insurance: [] }
}

// The same items as stored in localStorage before a data update
const staleWeapon = { id: 'Weapon_Test', name: 'Test SMG', baseStats: { Damage: 50, Weight: 20 } }
const staleOil = { id: 'Shaved_Clip_Oil', name: 'Shaved Clip Oil', modifiers: [{ attribute: 'ReloadSpeed', modType: 200, value: 0.5 }] }
const staleScroll = { id: 'Scroll_of_Light', name: 'Scroll of Light', modifiers: [{ attribute: 'RPM', modType: 200, value: -0.5 }] }
const staleScope = { id: 'Sniper_Scope', name: 'Sniper Scope', type: 'sight', modifiers: { ADSCritChance: 30 } }
const removedOil = { id: 'Cut_Oil', name: 'Cut Oil', modifiers: [] }
const noAttachments = { muzzle: null, sight: null, laser: null, chamber: null, chisel: null, insurance: null }

test('a stored item is replaced by the current item with the same id', () => {
  assert.equal(refreshItem(staleWeapon, data.weapons), weapon)
})

test('a stored item without an id is matched by name', () => {
  assert.equal(refreshItem({ name: 'Test SMG', baseStats: {} }, data.weapons), weapon)
})

test('a stored item that no longer exists in the data is kept as it was', () => {
  assert.equal(refreshItem(removedOil, data.oils), removedOil)
})

test('nothing selected stays nothing', () => {
  assert.equal(refreshItem(null, data.weapons), null)
})

test('before the data has loaded the stored item is kept', () => {
  assert.equal(refreshItem(staleWeapon, []), staleWeapon)
})

test('a list of stored items is refreshed item by item', () => {
  assert.deepEqual(refreshItems([staleOil, removedOil], data.oils), [oil, removedOil])
})

test('a list that is already current is returned as the same array', () => {
  const current = [oil, otherOil]
  assert.equal(refreshItems(current, data.oils), current)
})

test('stored attachments are refreshed within their slot', () => {
  const refreshed = refreshAttachments({ ...noAttachments, sight: staleScope }, data.attachmentsByType)
  assert.equal(refreshed.sight, scope)
  assert.equal(refreshed.muzzle, null)
})

test('attachments that are already current are returned as the same object', () => {
  const current = { ...noAttachments, sight: scope }
  assert.equal(refreshAttachments(current, data.attachmentsByType), current)
})

test('a saved build is refreshed as a whole and keeps its own fields', () => {
  const saved = {
    name: 'My build', timestamp: 123,
    weapon: staleWeapon, oils: [staleOil], scroll: staleScroll,
    attachments: { ...noAttachments, sight: staleScope }
  }
  const refreshed = refreshBuild(saved, data)
  assert.equal(refreshed.name, 'My build')
  assert.equal(refreshed.timestamp, 123)
  assert.equal(refreshed.weapon, weapon)
  assert.deepEqual(refreshed.oils, [oil])
  assert.equal(refreshed.scroll, scroll)
  assert.equal(refreshed.attachments.sight, scope)
})

test('a saved build from before attachments existed still refreshes', () => {
  const refreshed = refreshBuild({ name: 'Old', weapon: staleWeapon, oils: [], scroll: null }, data)
  assert.equal(refreshed.weapon, weapon)
  assert.equal(refreshed.attachments, undefined)
})

test('a build that is already current is returned as the same object', () => {
  const current = { name: 'Current', weapon, oils: [oil], scroll, attachments: { ...noAttachments, sight: scope } }
  assert.equal(refreshBuild(current, data), current)
})
