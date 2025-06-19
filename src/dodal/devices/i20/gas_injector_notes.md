
# Detectors

BL20I-EA-IAMP-01 = i0
04 = i1
02 = it
03 = iref

BL20I-EA-GIR-01:VACP1:CON is the pump - on, off, reset

## table

BL20I-EA-TABLE-02:X.VAL with x, y, sample rotation, fine rotation

also MO-Table-03 with 6 degrees of movement

t1 opticts table EA-01
with x, y

## diagram

scientifically we do small portion of the heavy gas to measure flux
we use the light gas (Helium) to make sure that the pressure is positive so that
we do not get air leak into the ion chamber.

```mermaid
flowchart TD
    title([BL20I-EA-GIR-01 - Gas Injection Rig])

    subgraph Inputs
        %% Inputs
        Kr[Kr] --> KrV[Valve 1]
        N2[N2] --> N2V[Valve 2]
        Ar[Ar] --> ArV[Valve 3]

        %% He input goes directly to Pressure 2
        He[He] 
    end

    %% Pressure 1 Loop
    KrV --> P1[Pressure 1]
    N2V --> P1
    ArV --> P1

    He[He] --> HeV[Valve PCTRL2] --> P2
    P1 --> VToP2[Valve to Pressure 2] --> P2[Pressure 2]

    P1 --> ReadoutP1[readout 01:P1] --> Pump[Pump with on off reset]

    P1 --> V4[Top closed loop V4] --> P1
    P1 --> V5[Pump side closed loop V5] --> P1


    %% Outputs from Pressure 2
    P2 --> V6[Valve 6] --> ReadoutP2[Readout P2, between the valve and ionc 1715 mBar] --> IONC1[IONC1 i0]
    P2 --> V7[Valve 7] --> ReadoutP3[Readout P3, between the valve and ionc 1713 mBar] --> IONC2[IONC2  - it]
    P2 --> V8[Valve 8] --> ReadoutP4[Readout P4, between the valve and ionc 1692 mBar] --> IONC3[IONC3  - iref]
    P2 --> V9[Valve 9] --> ReadoutP5[Readout P5, between the valve and ionc 1611 mBar] --> IONC4[IONC4  - i1]

    title -.-> Kr
    title -.-> N2
    title -.-> Ar
    title -.-> He
```
