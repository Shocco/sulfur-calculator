import { test } from 'node:test'
import assert from 'node:assert/strict'
import { getCompatibleAttachments, pruneIncompatibleAttachments } from './attachments.js'

// Fixtures mirror the shapes in public/data/*.json
const barrel = { name: 'Barrel Extension 6"', type: 'muzzle' }
const brake = { name: 'A12C Muzzle Brake', type: 'muzzle' }
const scope = { name: 'Sniper Scope', type: 'sight' }
const primingBolt = { name: 'Priming Bolt', type: 'chamber' }
const gunCrank = { name: 'Gun Crank', type: 'chamber' }

const attachmentsByType = {
  muzzle: [barrel, brake],
  sight: [scope],
  laser: [],
  chamber: [gunCrank, primingBolt],
  chisel: [],
  insurance: []
}
const notLoadedYet = { muzzle: [], sight: [], laser: [], chamber: [], chisel: [], insurance: [] }

const smg = {
  name: 'Ploika Compact',
  allowedAttachments: ['muzzle', 'sight', 'laser', 'chamber', 'chisel', 'insurance'],
  specificAttachments: ['Priming Bolt']
}
const energyGun = {
  name: 'D4RT',
  allowedAttachments: ['laser', 'sight', 'insurance'],
  specificAttachments: []
}
const crankGun = {
  name: 'Salamander',
  allowedAttachments: ['muzzle', 'sight', 'laser', 'chamber', 'chisel', 'insurance'],
  specificAttachments: ['Gun Crank']
}

const none = { muzzle: null, sight: null, laser: null, chamber: null, chisel: null, insurance: null }

test('a slot is narrowed to the weapon-specific attachments that belong to it', () => {
  assert.deepEqual(getCompatibleAttachments(smg, 'chamber', attachmentsByType.chamber), [primingBolt])
})

test('a slot with no weapon-specific attachments offers everything', () => {
  assert.deepEqual(getCompatibleAttachments(smg, 'muzzle', attachmentsByType.muzzle), [barrel, brake])
})

test('switching weapon drops attachments in slots the new weapon lacks', () => {
  const selected = { ...none, muzzle: barrel, sight: scope, chamber: primingBolt }
  const pruned = pruneIncompatibleAttachments(energyGun, selected, attachmentsByType)
  assert.deepEqual(pruned, { ...none, sight: scope })
})

test('switching weapon drops an attachment the new weapon does not accept in that slot', () => {
  const selected = { ...none, muzzle: barrel, chamber: primingBolt }
  const pruned = pruneIncompatibleAttachments(crankGun, selected, attachmentsByType)
  assert.deepEqual(pruned, { ...none, muzzle: barrel })
})

test('compatible attachments are kept and the same object is returned', () => {
  const selected = { ...none, muzzle: barrel, sight: scope, chamber: primingBolt }
  assert.equal(pruneIncompatibleAttachments(smg, selected, attachmentsByType), selected)
})

test('before attachment data has loaded only the slot check applies', () => {
  const selected = { ...none, muzzle: barrel, chamber: primingBolt }
  assert.equal(pruneIncompatibleAttachments(crankGun, selected, notLoadedYet), selected)
  assert.deepEqual(pruneIncompatibleAttachments(energyGun, selected, notLoadedYet), none)
})

test('no weapon selected leaves the selection alone', () => {
  const selected = { ...none, muzzle: barrel }
  assert.equal(pruneIncompatibleAttachments(null, selected, attachmentsByType), selected)
})
