import 'package:flutter/material.dart';

class CameraMask extends StatelessWidget {
  final int numColunas;

  const CameraMask({super.key, required this.numColunas});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final width = constraints.maxWidth;

        List<Widget> linhas = [];

        if (numColunas == 2) {
          linhas.add(_buildLinha(width / 2));
        } else if (numColunas == 3) {
          linhas.add(_buildLinha(width / 3));
          linhas.add(_buildLinha(2 * width / 3));
        }

        return Stack(children: linhas);
      },
    );
  }

  Widget _buildLinha(double left) {
    return Positioned(
      left: left - 0.5,
      top: 0,
      bottom: 0,
      child: Container(
        width: 1,
        color: Colors.greenAccent.withOpacity(0.3),
      ),
    );
  }
}
