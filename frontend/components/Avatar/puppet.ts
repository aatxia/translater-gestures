/**
 * Procedural primitive-based humanoid puppet for the placeholder 3D avatar
 * (Phase 15). No rigged/skinned GLTF asset -- just a handful of Three.js
 * primitives (sphere head, cylinder torso/limbs) parented into a joint-pivot
 * `Object3D` hierarchy, so poses.ts's rotations can drive it directly.
 *
 * Pure scene-graph construction: builds `THREE.Object3D`s but never touches
 * a canvas/WebGL context, so it's unit-testable without a real GPU (unlike
 * `THREE.WebGLRenderer`, which Avatar.tsx wraps separately with a fallback).
 */
import * as THREE from "three";
import type { JointRotations } from "./poses";

export interface Puppet {
  root: THREE.Group;
  head: THREE.Object3D;
  leftShoulder: THREE.Object3D;
  leftElbow: THREE.Object3D;
  rightShoulder: THREE.Object3D;
  rightElbow: THREE.Object3D;
}

function buildArm(sign: 1 | -1, material: THREE.Material): { shoulder: THREE.Group; elbow: THREE.Group } {
  const shoulder = new THREE.Group();
  shoulder.position.set(sign * 0.45, 1.0, 0);

  const upperArm = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 0.5, 12), material);
  upperArm.position.y = -0.25;
  shoulder.add(upperArm);

  const elbow = new THREE.Group();
  elbow.position.y = -0.5;
  shoulder.add(elbow);

  const forearm = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, 0.45, 12), material);
  forearm.position.y = -0.225;
  elbow.add(forearm);

  return { shoulder, elbow };
}

export function buildPuppet(): Puppet {
  const root = new THREE.Group();
  const bodyMaterial = new THREE.MeshStandardMaterial({ color: 0x6366f1 });
  const limbMaterial = new THREE.MeshStandardMaterial({ color: 0x818cf8 });

  const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.45, 1.1, 16), bodyMaterial);
  torso.position.y = 0.55;
  root.add(torso);

  const headPivot = new THREE.Group();
  headPivot.position.set(0, 1.1, 0);
  const headMesh = new THREE.Mesh(new THREE.SphereGeometry(0.28, 16, 16), bodyMaterial);
  headMesh.position.y = 0.28;
  headPivot.add(headMesh);
  root.add(headPivot);

  const left = buildArm(-1, limbMaterial);
  const right = buildArm(1, limbMaterial);
  root.add(left.shoulder, right.shoulder);

  return {
    root,
    head: headPivot,
    leftShoulder: left.shoulder,
    leftElbow: left.elbow,
    rightShoulder: right.shoulder,
    rightElbow: right.elbow,
  };
}

export function applyRotations(puppet: Puppet, rotations: JointRotations): void {
  puppet.head.rotation.set(rotations.head.x, rotations.head.y, 0);
  puppet.leftShoulder.rotation.set(rotations.leftShoulder.x, 0, rotations.leftShoulder.z);
  puppet.leftElbow.rotation.set(rotations.leftElbow, 0, 0);
  puppet.rightShoulder.rotation.set(rotations.rightShoulder.x, 0, rotations.rightShoulder.z);
  puppet.rightElbow.rotation.set(rotations.rightElbow, 0, 0);
}
