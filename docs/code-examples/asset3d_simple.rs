//! Log a simple 3D asset.

use rerun::external::anyhow;

fn main() -> anyhow::Result<()> {
    let args = std::env::args().collect::<Vec<_>>();
    let Some(path) = args.get(1) else {
        anyhow::bail!("Usage: {} <path_to_asset.[gltf|glb]>", args[0]);
    };

    let (rec, storage) =
        rerun::RecordingStreamBuilder::new("rerun_example_asset3d_simple").memory()?;

    rec.log_timeless("world", &rerun::ViewCoordinates::RIGHT_HAND_Z_UP)?; // Set an up-axis
    rec.log("world/asset", &rerun::Asset3D::from_file(path)?)?;

    rerun::native_viewer::show(storage.take())?;
    Ok(())
}
